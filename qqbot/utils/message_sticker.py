import base64
import re
from dataclasses import dataclass


@dataclass
class FaceTypeTag:
    raw: str
    faceType: str
    faceId: int
    ext: str | None
    encoded_ext: str | None


def extract_faceType_tags(text):
    result_list = []
    # 1) 先提取出所有 faceType 标签块
    tag_pattern = re.compile(r"<faceType=[^>]+>")

    # 2) 再解析标签内部的 key=value 对（值可能有引号，也可能没有）
    attr_pattern = re.compile(r'(\w+)\s*=\s*(?:"([^"]*)"|([^,>\s]+))')

    for tag in tag_pattern.findall(text):
        print(tag)  # 输出: <faceType=1,faceId="178",ext="eyJ0ZXh0Ijoi5q2q56yRIn0=">
        inner = tag[1:-1]  # 去掉首尾的 < >
        attrs = {}
        for m in attr_pattern.finditer(inner):
            key = m.group(1)
            # 有引号取值 group(2)，无引号取值 group(3)
            value = m.group(2) if m.group(2) is not None else m.group(3)
            attrs[key] = value
        print(attrs)

        base64_str = attrs.get("ext")
        decoded_str = None
        if base64_str:
            decoded_bytes = base64.b64decode(base64_str)
            decoded_str = decoded_bytes.decode("utf-8")
            print(decoded_str)  # 输出: {"text":"测试"}

        result = FaceTypeTag(
            raw=tag,
            faceType=attrs.get("faceType", 1),
            faceId=int(attrs.get("faceId", 0)),
            ext=base64_str,
            encoded_ext=decoded_str,
        )
        result_list.append(result)

    return result_list


# 输出: {'faceType': '1', 'faceId': '178', 'ext': 'eyJ0ZXh0Ijoi5q2q56yRIn0='}

if __name__ == "__main__":
    text = '普通文本<faceType=1,faceId="178",ext="eyJ0ZXh0Ijoi5q2q56yRIn0=">>efefewfw>后续文字<@87A58E0FB1BD6DB6CBF1AFEB9C48D8FA><faceType=1,faceId="178",ext="eyJ0ZXh0Ijoi5q2q56yRIn0=">'
    print(extract_faceType_tags(text))
