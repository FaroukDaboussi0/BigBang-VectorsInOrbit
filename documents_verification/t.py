import nbformat

nb = nbformat.read("D:\hackaton2026\documents_verification\QdrantIDCard.ipynb", as_version=4)

if "widgets" in nb.metadata:
    nb.metadata.pop("widgets")

nbformat.write(nb, "D:\hackaton2026\documents_verification\QdrantIDCard_2.ipynb")
