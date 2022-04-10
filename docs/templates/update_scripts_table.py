#!/usr/bin/env python3
""" 
Automates creating markdown table from excel sheet
and pushing it to README.md
"""
import xlsx_to_md
import compiler


def main():
    xlsx_to_md.driver()
    compiler.driver()


if __name__ == "__main__":
    main()
