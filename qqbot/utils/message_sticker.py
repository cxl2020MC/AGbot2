import re

text = '普通文本<faceType=1,faceId="178",ext="eyJ0ZXh0Ijoi5q2q56yRIn0=">后续文字<@87A58E0FB1BD6DB6CBF1AFEB9C48D8FA><faceType=1,faceId="178",ext="eyJ0ZXh0Ijoi5q2q56yRIn0=">'

# 1) 先提取出所有 faceType 标签块
tag_pattern = re.compile(r'<faceType=[^>]+>')

# 2) 再解析标签内部的 key=value 对（值可能有引号，也可能没有）
attr_pattern = re.compile(r'(\w+)=(?:"([^"]*)"|([^,>]+))')

for tag in tag_pattern.findall(text):
    inner = tag[1:-1]  # 去掉首尾的 < >
    attrs = {}
    for m in attr_pattern.finditer(inner):
        key = m.group(1)
        # 有引号取值 group(2)，无引号取值 group(3)
        value = m.group(2) if m.group(2) is not None else m.group(3)
        attrs[key] = value
    print(attrs)

# 输出: {'faceType': '1', 'faceId': '178', 'ext': 'eyJ0ZXh0Ijoi5q2q56yRIn0='}