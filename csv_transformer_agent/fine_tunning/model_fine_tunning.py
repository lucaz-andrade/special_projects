from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import numpy as np

# Carregar o tokenizer e o modelo
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')


# Preparar o texto para treinamento
textos = [
  "merchant-order-id",
  "purchase-date",
  "ship-city",
  "ship-state",
  "ship-postal-code",
  "sku",

  "Order ID",
  "Order Date",
  "Shipping Street 1",
  "Shipping Street 2",
  "Shipping Suburb",
  "Shipping State Abbreviation",
  "Shipping Zip",

  "Invoice number",
  "Num",
  "Invoice date",
  "Date",
  "Shipping address",
  "Shipping address_1",
  "Billing address",
  "Shipping city",
  "Shipping city_1",
  "Billing city",
  "Shipping state",
  "Shipping state_1",
  "Billing state",
  "shipping zip code",
  "shipping zip code_1",
  "billing zip code",

  "Unique Identifier",
  "payment_metadata[order_id]",
  "id",
  "transaction_date",
  "destination_resolved_address_line1",
  "destination_resolved_address_line2",
  "destination_resolved_address_city",
  "destination_resolved_address_state",
  "destination_resolved_address_postal_code"
]


# Preparar os labels para treinamento
labels = [
  "transactionId",
  "transactionDate",
  "shipToCity",
  "shipToState",
  "shipToZip",
  "lineItemProductName",

  "transactionId",
  "transactionDate",
  "shipToAddress1",
  "shipToAddress2",
  "shipToCity",
  "shipToState",
  "shipToZip",

  "transactionId",
  "transactionId",
  "transactionDate",
  "transactionDate",
  "shipToAddress1",
  "shipToAddress1",
  "shipToAddress1",
  "shipToCity",
  "shipToCity",
  "shipToCity",
  "shipToState",
  "shipToState",
  "shipToState",
  "shipToZip",
  "shipToZip",
  "shipToZip",


  "transactionId",
  "transactionId",
  "transactionId",
  "transactionDate",
  "shipToAddress1",
  "shipToAddress2",
  "shipToCity",
  "shipToState",
  "shipToZip"
]

model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=len(set(labels)))
# Converter labels para números
label_encoder = LabelEncoder()
numeric_labels = label_encoder.fit_transform(labels)

# Dividir dados em treino e teste
X_train, X_test, y_train, y_test = train_test_split(textos, numeric_labels, test_size=0.2, random_state=42)

# Tokenizar os textos
def tokenize_data(texts):
    return tokenizer(texts, padding=True, truncation=True, return_tensors="pt", max_length=128)

# Preparar dados de treino
train_encodings = tokenize_data(X_train)
train_dataset = TensorDataset(
    train_encodings['input_ids'],
    train_encodings['attention_mask'],
    torch.tensor(y_train)
)

# Preparar dados de teste
test_encodings = tokenize_data(X_test)
test_dataset = TensorDataset(
    test_encodings['input_ids'],
    test_encodings['attention_mask'],
    torch.tensor(y_test)
)

# Configurar DataLoader
train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=8)

# Configurar otimizador
optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)

# Função de treinamento
def train_model(model, train_loader, optimizer, epochs=5):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    model.to(device)
    model.train()
    
    for epoch in range(epochs):
        total_loss = 0
        for batch in train_loader:
            input_ids = batch[0].to(device)
            attention_mask = batch[1].to(device)
            labels = batch[2].to(device)
            
            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(train_loader)}")
    
    return model

# Função de avaliação
def evaluate_model(model, test_loader):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    model.eval()
    
    correct = 0
    total = 0
    
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch[0].to(device)
            attention_mask = batch[1].to(device)
            labels = batch[2].to(device)
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            _, predicted = torch.max(outputs.logits, 1)
            
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    
    accuracy = correct / total
    print(f"Accuracy: {accuracy:.4f}")
    return accuracy

# Treinar o modelo
print("Starting training...")
model = train_model(model, train_loader, optimizer)

# Avaliar o modelo
print("Evaluating model...")
evaluate_model(model, test_loader)

# Salvar o modelo treinado
model_path = "distilbert_column_classifier"
model.save_pretrained(model_path)
tokenizer.save_pretrained(model_path)
print(f"Model saved to {model_path}")

# Função para fazer previsões em novos dados
def predict(text):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    model.eval()
    
    inputs = tokenizer(text, padding=True, truncation=True, return_tensors="pt", max_length=128)
    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)
    
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        predictions = torch.argmax(outputs.logits, dim=1).cpu().numpy()
    
    return label_encoder.inverse_transform(predictions)

# Exemplo de uso da função de previsão
example_texts = ["customer-id", "order-date", "shipping-address"]
predictions = predict(example_texts)
for text, pred in zip(example_texts, predictions):
    print(f"Text: '{text}' → Predicted: '{pred}'")
