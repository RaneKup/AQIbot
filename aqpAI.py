import torch
import torch.nn as nn
import pandas as pd
import numpy as np

checkpoint = torch.load('kemerovo_model.pth', weights_only=False)
scaler = checkpoint['scaler']

lstm_layer = nn.LSTM(input_size=4, hidden_size=64, num_layers=1, batch_first=True)
fc_layer = nn.Linear(64, 1)

lstm_layer.load_state_dict(checkpoint['lstm_state'])
fc_layer.load_state_dict(checkpoint['fc_state'])
lstm_layer.eval()

df = pd.read_csv('kemerovo_data.csv')
last_hours = df[['pm2_5', 'temp', 'hum', 'wind']].ffill().bfill().values[-24:]
current_batch = scaler.transform(last_hours)
current_batch = torch.tensor(current_batch, dtype=torch.float32).unsqueeze(0)

forecast_results = []
input_seq = current_batch.clone()

with torch.no_grad():
    for _ in range(24):
        lstm_out, (hn, cn) = lstm_layer(input_seq)
        pred = fc_layer(hn[-1])

        forecast_results.append(pred.item())

        next_step_features = input_seq[:, -1, :].clone()
        next_step_features[0, 0] = pred.item()

        input_seq = torch.cat((input_seq[:, 1:, :], next_step_features.unsqueeze(1)), dim=1)

dummy = np.zeros((24, 4))
dummy[:, 0] = forecast_results
final_forecast = scaler.inverse_transform(dummy)[:, 0]

# print("--- Прогноз качества воздуха (PM2.5) на 24 часа ---")
# for i, val in enumerate(final_forecast, 1):
#     status = "ОПАСНО" if val > 50 else "НОРМА"
#     print(f"Час {i:02d}: {val:6.2f} µg/m³ | {status}")

dummy = np.zeros((24, 4))
dummy[:, 0] = forecast_results
final_forecast = scaler.inverse_transform(dummy)[:, 0]

average_pm25 = np.mean(final_forecast)

print(f"--- Результат прогноза на завтра ---")
print(f"Среднесуточная концентрация PM2.5: {average_pm25:.2f} µg/m³")

if average_pm25 > 15:
    print("Статус: Ожидается превышение нормы загрязнения.")
else:
    print("Статус: Воздух будет в пределах нормы.")