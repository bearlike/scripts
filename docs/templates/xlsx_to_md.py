#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pytablewriter import MarkdownTableWriter


def write_to_md(headers, data, filename="scripts.md.j2"):
    # Data to Markdown
    writer = MarkdownTableWriter(
        table_name="", headers=headers, value_matrix=data, margin=1)
    writer.dump(filename)
    print(f"Wrote to {filename}.....")


def read_excel(filename="../scripts.xls"):
    print(f"Reading {filename}.....")
    df = pd.read_excel(filename)
    headers = list(df.columns.values)
    data = df.values.tolist()
    # Remove NaN values in the list
    for idx, _ in enumerate(data):
        for jdx, _ in enumerate(data[idx]):
            if data[idx][jdx] is np.nan:
                data[idx][jdx] = " "
    return headers, data


def driver():
    headers, data = read_excel()
    write_to_md(headers, data)


if __name__ == "__main__":
    driver()
