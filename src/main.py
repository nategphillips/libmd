# module main
"""
Produces formatted Markdown tables from CSV data.
"""

from pathlib import Path

import pandas as pd

# Enable copy-on-write since it will become the default in Pandas 3.0
# https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pd.options.mode.copy_on_write = True


def get_last_names(authors: str) -> str:
    """
    Takes in a string of authors and returns their last names.
    """

    # First, split the authors by the word "and", then further split them by commas; finally, add
    # them to the list if the string is not empty
    author_list: list[str] = [
        author.strip() for part in authors.split(" and ") for author in part.split(",") if author
    ]

    formatted_authors: list[str] = []

    for author in author_list:
        # Handle the special case where "et al." is present in the author's name and just add the
        # entire string to the formatted authors list
        if "et al." in author:
            formatted_authors.append(author)
        else:
            # Split name by spaces
            parts: list[str] = author.split()

            if parts:
                # If the name exists, assume the last part is the last name
                last_name: str = parts[-1]
                # Handle the special case where "Jr." is present in the author's name by taking the
                # second to last element as the last name
                if parts[-1] == "Jr.":
                    last_name = parts[-2]

                formatted_authors.append(last_name)

    # If there are multiple authors, separate them with spaces and add an ampersand between the last
    # two
    if len(formatted_authors) > 1:
        return ", ".join(formatted_authors[:-1]) + " & " + formatted_authors[-1]

    return formatted_authors[0]


def md_from_csv(csv_path: Path, md_path: Path):
    """
    Creates and writes to a Markdown file using data from the provided CSV file.
    """

    df = pd.read_csv(csv_path, dtype={"Pages": str, "ISBN-13": str})

    # Extract the unique categories, sort them alphabetically, and convert to a list of strings
    categories: list[str] = sorted(df["Category"].unique())

    with open(md_path, mode="w", encoding="utf-8") as f:
        for category in categories:
            f.write(f"## {category}\n\n")

            # Filter the data for the current category only
            category_df: pd.DataFrame = df[df["Category"] == category]

            # Use .loc to add a new column for last names
            category_df.loc[:, "Last Names"] = category_df["Author(s)"].apply(get_last_names)

            # First sort by first author's last name, then sort by title
            sorted_df: pd.DataFrame = category_df.sort_values(by=["Last Names", "Title"])

            f.write("| Author | Title | ISBN |\n")
            f.write("| ------ | ----- | ---- |\n")

            for _, row in sorted_df.iterrows():
                last_names: str = str(row["Last Names"])
                title: str = str(row["Title"])
                isbn_type: str = str(row["ISBN-10"])
                isbn: str = str(row["ISBN-13"])

                if isbn_type == "Pre-ISBN":
                    f.write(f"| {last_names} | *{title}* | Pre-ISBN |\n")
                elif isbn_type == "No ISBN":
                    f.write(f"| {last_names} | *{title}* | No ISBN |\n")
                elif isbn_type == "LCCN":
                    f.write(f"| {last_names} | *{title}* | LCCN: {isbn} |\n")
                else:
                    f.write(f"| {last_names} | *{title}* | {isbn} |\n")

            f.write("\n")


def main() -> None:
    """
    Entry point.
    """

    csv_path: Path = Path("../data/example.csv")
    md_path: Path = Path("../data/example.md")

    md_from_csv(csv_path, md_path)

    print(f"Markdown file '{md_path}' has been created.")


if __name__ == "__main__":
    main()
