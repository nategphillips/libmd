# module main
"""
Produces formatted Markdown tables from CSV data.
"""

from pathlib import Path

import pandas as pd


def get_last_names(authors: str) -> str:
    """
    Takes in a string of authors and returns their last names.
    """

    # Split authors by commas and add them to the list if the string is not empty
    author_list = [author.strip() for author in str(authors).split(",") if author.strip()]

    def helper(name: str) -> str:
        parts = name.split()

        if not parts:
            return ""

        # Should probably extend this to cover more than just "Jr.", but for now this is all I need
        return parts[-2] if parts[-1] == "Jr." and len(parts) >= 2 else parts[-1]

    formatted_authors = []

    for author in author_list:
        et_al = "et al." in author

        # Assume only a single "author" exists, something like "Marcus Tullius Cicero et al.", and
        # remove the "et al." to get the actual name
        author = author.replace("et al.", "").strip()
        last_name = helper(author)

        if last_name:
            formatted_authors.append(f"{last_name} et al." if et_al else last_name)

    # If there are multiple authors, separate them with spaces and add an ampersand between the last
    # two
    if len(formatted_authors) > 1:
        return ", ".join(formatted_authors[:-1]) + " & " + formatted_authors[-1]

    return formatted_authors[0]


def write_table(f, books_df: pd.DataFrame) -> None:
    """
    Writes a Markdown table for the provided dataframe.
    """

    if books_df.empty:
        return

    books_df = books_df.copy()

    # Use .loc to add a new column for last names
    books_df.loc[:, "Last Names"] = books_df["Author(s)"].apply(get_last_names)

    # First sort by first author's last name, then sort by title
    sorted_df = books_df.sort_values(by=["Last Names", "Title"])

    f.write("| Author | Title | ISBN |\n")
    f.write("| ------ | ----- | ---- |\n")

    for _, row in sorted_df.iterrows():
        last_names = row["Last Names"]
        title = row["Title"]
        isbn_type = row["ISBN-10"]
        isbn = row["ISBN-13"]

        if isbn_type == "Pre-ISBN":
            f.write(f"| {last_names} | *{title}* | Pre-ISBN |\n")
        elif isbn_type == "No ISBN":
            f.write(f"| {last_names} | *{title}* | No ISBN |\n")
        elif isbn_type == "LCCN":
            f.write(f"| {last_names} | *{title}* | LCCN: {isbn} |\n")
        elif isbn_type == "DOI":
            f.write(f"| {last_names} | *{title}* | DOI: {isbn} |\n")
        else:
            f.write(f"| {last_names} | *{title}* | {isbn} |\n")

    f.write("\n")


def md_from_csv(csv_path: Path, md_path: Path) -> None:
    """
    Creates and writes to a Markdown file using data from the provided CSV file.
    """

    df = pd.read_csv(csv_path, dtype={"Pages": str, "ISBN-13": str})
    # Only extract books in my physical collection, others are marked as "Want"
    df = df[df["Status"].astype(str).str.strip().eq("Have")].copy()

    # Remove the troublesome `-` character for blank sub-category fields
    df["Sub-category"] = df["Sub-category"].fillna("-").astype(str).str.strip()

    # Extract the unique categories, sort them alphabetically, and convert to a list of strings
    categories = sorted(df["Category"].unique())

    with open(md_path, mode="w", encoding="utf-8") as f:
        for category in categories:
            f.write(f"## {category}\n\n")

            # Filter the data for the current category only
            category_df = df[df["Category"] == category].copy()

            # Books without a sub-category go directly under the category
            no_sub_category_df = category_df[category_df["Sub-category"] == "-"]

            write_table(f, no_sub_category_df)

            # Create sub-headings
            sub_categories = sorted(
                category_df.loc[category_df["Sub-category"] != "-", "Sub-category"].unique()
            )

            for sub_category in sub_categories:
                f.write(f"### {sub_category}\n\n")

                sub_category_df = category_df[category_df["Sub-category"] == sub_category]

                write_table(f, sub_category_df)


def main() -> None:
    """
    Entry point.
    """

    csv_path = Path("../data/example.csv")
    md_path = Path("../data/example.md")

    md_from_csv(csv_path, md_path)

    print(f"Markdown file '{md_path}' has been created.")


if __name__ == "__main__":
    main()
