import openpyxl
from pathlib import Path

wb = openpyxl.Workbook()
ws = wb.active
ws.append(["Code", "Name"])
ws.append(["QATEST1", "QA Test Department One"])
ws.append(["QATEST2", "QA Test Department Two"])
ws.append(["QATEST1", "QA Test Department One"])
ws.append(["EXISTING", "Pre-seeded department for existing-check"])
ws.append(["", "Missing Code Department"])
ws.append(["QATEST3", ""])
wb.save(Path(__file__).parent / "departments.xlsx")
print("departments.xlsx generated")
