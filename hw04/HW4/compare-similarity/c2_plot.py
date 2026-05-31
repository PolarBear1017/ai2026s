import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 設定要讀取的資料夾
csv_folder = 'excel'

# 取得所有 CSV 檔案
csv_files = [f for f in os.listdir(csv_folder) if f.lower().endswith('.csv')]

if not csv_files:
    raise ValueError(f"錯誤：資料夾 {csv_folder} 內沒有 CSV 檔案！")

for csv_file in csv_files:
    csv_path = os.path.join(csv_folder, csv_file)
    df = pd.read_csv(csv_path)

    # 確保必要欄位存在
    required_columns = {'Student', 'LPIPS', 'SSIM'}
    if not required_columns.issubset(df.columns):
        print(f"警告：{csv_file} 缺少必要欄位，跳過此檔案。")
        continue  

    # 檢查原始數據範圍
    print(f"{csv_file} - SSIM 範圍: {df['SSIM'].min()} ~ {df['SSIM'].max()}, LPIPS 範圍: {df['LPIPS'].min()} ~ {df['LPIPS'].max()}")

    my_data = pd.DataFrame({'Student': ['Mine'], 'LPIPS': [0.0], 'SSIM': [1.0]})
    df = pd.concat([df, my_data], ignore_index=True)

    # 建立一個顏色分類標籤分紅綠
    df['Color_Type'] = df['Student'].apply(lambda x: 'Self' if x == 'Mine' else 'Others')

    # 篩選數據
    df_filtered = df[(df['SSIM'] >= 0) & (df['SSIM'] <= 1) & 
                     (df['LPIPS'] >= 0) & (df['LPIPS'] <= 1)]

    # 如果篩選後沒數據，跳過繪圖
    if df_filtered.empty:
        print(f"{csv_file} 無符合條件的數據，跳過繪圖。")
        continue

    # 設定圖片大小
    plt.figure(figsize=(12, 8))
    plt.title(f'Scatter - SSIM vs LPIPS ({csv_file})', fontsize=14)

    # 繪製散點圖
    custom_palette = {'Self': 'red', 'Others': 'green'}
    
    scatter = sns.scatterplot(
        data=df_filtered, 
        x='SSIM', 
        y='LPIPS', 
        hue='Color_Type',
        palette=custom_palette, 
        s=100,
        edgecolor='w',
        legend=True
    )

    # 加入標籤（偏移一點，避免重疊）
    for index, row in df_filtered.iterrows():
        plt.text(row['SSIM'] + 0.005, row['LPIPS'], 
                 row['Student'], horizontalalignment='left', 
                 fontsize=9, color='black', weight='semibold')

    # 設定 X 軸與 Y 軸範圍（根據數據動態調整）
    plt.xlim(df_filtered['SSIM'].min() - 0.02, df_filtered['SSIM'].max() + 0.02)
    plt.ylim(df_filtered['LPIPS'].min() - 0.02, df_filtered['LPIPS'].max() + 0.02)

    # 設定 X/Y 軸標籤
    plt.xlabel('SSIM', fontsize=12)
    plt.ylabel('LPIPS', fontsize=12)

    # 儲存圖片
    image_filename = os.path.splitext(csv_file)[0] + ".png"
    image_path = os.path.join(csv_folder, image_filename)
    plt.savefig(image_path, bbox_inches='tight', dpi=300)
    print(f"圖片已儲存：{image_path}")

    # 顯示圖片
    plt.show()

print("所有 CSV 檔案的圖表已生成完畢！")
