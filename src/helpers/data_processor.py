
import pandas as pd

def read_diagnosis_data(filepath):
    df = pd.read_excel(filepath)
    return df

if __name__ == "__main__":
    df = read_diagnosis_data("radiologist_notes\\radiologist_report.xlsx")
    print(df.head())