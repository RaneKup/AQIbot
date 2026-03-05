import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

file_path = 'kemerovo_data.csv'

try:
    df = pd.read_csv(file_path)
    data = df[['pm2_5', 'temp', 'hum', 'wind']].ffill().bfill().values
    print(f"Файл успешно загружен. Строк для обучения: {len(df)}")
except FileNotFoundError:
    print(f"Ошибка: Файл '{file_path}' не найден в папке с проектом!")
    exit()

scaler = MinMaxScaler()
data_scaled = scaler.fit_transform(data)

look_back = 24
X, y = [], []
for i in range(len(data_scaled) - look_back):
    X.append(data_scaled[i:i + look_back])
    y.append(data_scaled[i + look_back, 0])

X_train = torch.tensor(np.array(X), dtype=torch.float32)
y_train = torch.tensor(np.array(y), dtype=torch.float32).view(-1, 1)

lstm_layer = nn.LSTM(input_size=4, hidden_size=64, num_layers=1, batch_first=True)
fc_layer = nn.Linear(64, 1)

optimizer = torch.optim.Adam(list(lstm_layer.parameters()) + list(fc_layer.parameters()), lr=0.001)
loss_fn = nn.MSELoss()

print("Начинаю обучение...")
for epoch in range(20):
    lstm_out, (hn, cn) = lstm_layer(X_train)
    predictions = fc_layer(hn[-1])

    loss = loss_fn(predictions, y_train)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if (epoch + 1) % 5 == 0:
        print(f"Эпоха {epoch + 1}/20, Ошибка (MSE): {loss.item():.6f}")

torch.save({
    'lstm_state': lstm_layer.state_dict(),
    'fc_state': fc_layer.state_dict(),
    'scaler': scaler
}, 'kemerovo_model.pth')

print("Обучение завершено. Модель сохранена в 'kemerovo_model.pth'")
