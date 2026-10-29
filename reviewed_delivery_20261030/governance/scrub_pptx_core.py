from pathlib import Path
import sys,zipfile,xml.etree.ElementTree as ET
p=Path(sys.argv[1]);target=p.with_name(p.stem+'-metadata.pptx')
with zipfile.ZipFile(p) as src,zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as dst:
    for info in src.infolist():
        data=src.read(info.filename)
        if info.filename=='docProps/core.xml':
            tree=ET.fromstring(data)
            for child in tree:
                name=child.tag.rsplit('}',1)[-1]
                if name in ['creator','lastModifiedBy']:child.text=''
                elif name=='title':child.text='AI导购理由撤回后的预算重审'
            data=ET.tostring(tree,encoding='utf-8',xml_declaration=True)
        dst.writestr(info,data)
