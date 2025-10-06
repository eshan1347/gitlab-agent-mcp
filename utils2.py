from copy import deepcopy
from typing import Any, Dict, Set, List
import json
from utils import fix_schema

def jsonConv(schema :Dict[str, Any]) -> Dict[str, Any]:
    schema = fix_schema(schema)
    val_prop_keys = ['type', 'description', 'enum', 'default', 'minimum', 'maximum', 'minLength', 'maxLength', 'pattern', 'items', 'format']
    # val_prop_keys = ['type', 'description']
    val_schema_keys = ['type', 'properties', 'required']
    res = {}
    for key in schema:
        # print(f'Schema Key: {key}')
        if key in val_schema_keys:
            if key == 'properties':
                res2 = {} 
                for prop in schema[key]:
                    # print(f'Prop : {prop}')
                    res3 = {}
                    for prop_key in schema[key][prop]:
                        # print(f'Prop key: {prop_key}')
                        if prop_key in val_prop_keys:
                            temp = schema[key][prop][prop_key]
                            # print(f'temp: {temp}')
                            if isinstance(temp, Dict) and prop_key != "items":
                                continue
                            if isinstance(temp, List):
                                for ty in temp:
                                    if ty in val_prop_keys:
                                        temp = ty
                                        break
                            res3[prop_key] = temp
                    if res3:
                        # print(f'Res3: {res3}')
                        res2[prop] = res3
                if res2:
                    # print(f'Res2: {res2}')
                    res[key] = res2
            else:
                res[key] = schema[key]
    return res

if __name__=='__main__':
    with open('./test.json', 'r') as f:
        jason = json.load(f)
    print(jsonConv(jason))