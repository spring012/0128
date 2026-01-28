import win32com.client as win32
from win32com.client import constants
import os

doc_app = win32.gencache.EnsureDispatch('Word.Application')
doc_app.Visible =1
doc = doc_app.Documents.Add(os.getcwd() + '\\test.docx')

parag_range = doc.Paragraphs(7).Range
parag_range.InsertAfter('Catelogs')
parag_range = doc.Paragraphs(8).Range
doc.TablesOfContents.Add(Range=parag_range, UseHeadingStyles=True,LowerHeadingLevel=3, UseHyperlinks=True)

doc.SaveAs(os.getcwd() + "\\funOpenNewFile.docx") 
doc.Close() 
doc_app.Quit()