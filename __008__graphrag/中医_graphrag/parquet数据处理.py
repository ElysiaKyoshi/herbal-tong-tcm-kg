import pandas as pd

documents = pd.read_parquet('./output/documents.parquet')
# print(documents)
documents.to_csv('./data_process/documents.csv')


text_units = pd.read_parquet('./output/text_units.parquet')
# print(documents)
text_units.to_csv('./data_process/text_units.csv')