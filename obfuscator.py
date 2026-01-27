import json
import random
import string
import re
import sys
import argparse
import os

class CatWebObfuscator:
    def __init__(self, word_file="./assets/words.txt"):
        self.symbol_map = {}
        self.used_symbols = set()
        self.global_ids = set()
        self.math_funcs = {}
        self.word_list = []
        
        if os.path.exists(word_file):
            with open(word_file, 'r') as f:
                self.word_list = [w.strip() for w in f.readlines() if w.strip().isalpha() and len(w.strip()) > 3]
        
    def generate_random_name(self):
        while True:
            if self.word_list:
                name = random.choice(self.word_list)
                if random.random() > 0.5:
                    name = name.capitalize()
            else:
                length = random.randint(5, 8)
                consonants = "bcdfghjklmnpqrstvwxyz"
                vowels = "aeiou"
                name = ""
                for i in range(length):
                    if i % 2 == 0:
                        name += random.choice(consonants)
                    else:
                        name += random.choice(vowels)
                if random.random() > 0.5:
                    name = name.capitalize()
                
            if name.lower() not in ["cat", "web", "roblox", "script", "parent", "parent?", "index", "value"]:
                if name not in self.used_symbols:
                    self.used_symbols.add(name)
                    return name

    def get_obfuscated_name(self, original_name):
        if original_name in [
            "(parent)", "l!index", "l!value", "messageContent", "messageSenderId", "messageSenderName",
            "Increase", "Decrease", "Multiply", "Divide", "pow", "mod", "round", "floor", "ceil", "pi", "huge",
            "sin", "cos", "tan", "asin", "acos", "atan", "atan2", "deg", "rad", "exp", "log", "log10", "sqrt", "abs"
        ]:
            return original_name
        
        prefix = ""
        actual_name = original_name
        if original_name.startswith("l!"):
            prefix = "l!"
            actual_name = original_name[2:]
        elif original_name.startswith("o!"):
            prefix = "o!"
            actual_name = original_name[2:]
        elif original_name.startswith("{") and original_name.endswith("}"):
            inner = original_name[1:-1]
            return "{" + self.get_obfuscated_name(inner) + "}"
            
        if actual_name not in self.symbol_map:
            self.symbol_map[actual_name] = self.generate_random_name()
            
        return prefix + self.symbol_map[actual_name]

    def generate_global_id(self):
        chars = string.ascii_letters + string.digits
        while True:
            gid = ''.join(random.choice(chars) for _ in range(random.randint(2, 4)))
            if gid not in self.global_ids:
                self.global_ids.add(gid)
                return gid

    def process_text_field(self, text_list):
        new_text = []
        for item in text_list:
            if isinstance(item, str):
                def replace_var_match(match):
                    var_name = match.group(1)
                    return "{" + self.process_identifier(var_name) + "}"
                
                def replace_table_var_match(match):
                    full_name = match.group(0)[1:-1]
                    parts = full_name.split('.')
                    parts[0] = self.process_identifier(parts[0])
                    return "{" + '.'.join(parts) + "}"

                item = re.sub(r'\{([a-zA-Z0-9_!]+)\}', replace_var_match, item)
                item = re.sub(r'\{([a-zA-Z0-9_!]+\.[a-zA-Z0-9_.]+)\}', replace_table_var_match, item)
                new_text.append(item)
            elif isinstance(item, dict):
                new_item = item.copy()
                val = item.get("value")
                t = item.get("t")
                l = item.get("l")

                if t == "tuple" and isinstance(val, list):
                    new_item["value"] = self.process_tuple(val)
                elif l in ["variable", "variable?", "table", "function"]:
                    new_item["value"] = self.get_obfuscated_name(val)
                elif isinstance(val, str):
                    new_item["value"] = self.obfuscate_string_value(val)
                
                new_text.append(new_item)
        return new_text

    def process_identifier(self, identifier):
        if "." in identifier:
            parts = identifier.split(".")
            parts[0] = self.get_obfuscated_name(parts[0])
            return ".".join(parts)
        return self.get_obfuscated_name(identifier)

    def obfuscate_string_value(self, val):
        val = re.sub(r'\[([ol]![a-zA-Z0-9_]+)\}', r'{\1}', val)
        
        def replace_var_match(match):
            var_name = match.group(1)
            return "{" + self.process_identifier(var_name) + "}"
        return re.sub(r'\{([a-zA-Z0-9_!.]+)\}', replace_var_match, val)

    def process_tuple(self, tuple_list):
        new_tuple = []
        for param in tuple_list:
            new_param = param.copy()
            val = param.get("value")
            
            if isinstance(val, str):
                new_param["value"] = self.obfuscate_string_value(val)
            elif isinstance(val, list):
                new_param["value"] = self.process_tuple(val)
                
            new_tuple.append(new_param)
        return new_tuple

    def obfuscate_action(self, action):
        action["globalid"] = self.generate_global_id()
        if "text" in action:
            action["text"] = self.process_text_field(action["text"])
            
        math_ids = {"12": "Increase", "13": "Decrease", "14": "Multiply", "15": "Divide"}
        action_id = str(action.get("id"))
        if action_id in math_ids:
            op_name = math_ids[action_id]
            if op_name in self.math_funcs:
                params = [item for item in action["text"] if isinstance(item, dict)]
                if len(params) >= 2:
                    var_param = params[0]
                    val_param = params[1]
                    target_var = var_param["value"]
                    
                    new_action = {
                        "id": "87",
                        "text": [
                            "Run function",
                            {"value": self.math_funcs[op_name], "t": "string", "l": "function"},
                            {
                                "value": [
                                    {"value": "{" + target_var + "}", "t": "any", "l": "any"},
                                    {"value": val_param["value"], "t": val_param.get("t", "any"), "l": "any"}
                                ],
                                "t": "tuple"
                            },
                            "→",
                            {"value": target_var, "l": "variable", "t": "string"}
                        ],
                        "globalid": self.generate_global_id()
                    }
                    return new_action
            
        return action

    def generate_dummy_action(self):
        length = random.randint(10, 25)
        consonants = "bcdfghjklmnpqrstvwxyz"
        vowels = "aeiou"
        text = ""
        for i in range(length):
            if i % 2 == 0:
                text += random.choice(consonants)
            else:
                text += random.choice(vowels)
            if i > 0 and i % 6 == 0 and random.random() > 0.5:
                text += " "
                
        return {
            "id": "124",
            "text": [{"value": text.strip(), "t": "string", "l": "comment"}],
            "globalid": self.generate_global_id()
        }

    def split_actions(self, actions, script_content, params=None, is_function=False):
        depth = 0
        processed_actions = []
        safe_points = [0]
        
        for idx, action in enumerate(actions):
            processed_actions.append(action)
            action_id = str(action.get("id"))
            
            if action_id in ["18", "19", "20", "21", "22"]:
                depth += 1
            elif action_id == "25":
                depth -= 1
            
            if depth == 0:
                safe_points.append(len(processed_actions))
                if random.random() < 0.1:
                    processed_actions.append(self.generate_dummy_action())
                    safe_points.append(len(processed_actions))

        actions = processed_actions
        
        if len(safe_points) <= 4 or len(actions) <= 15:
            return actions

        num_chunks = min(3, len(safe_points) // 4)
        split_indices = random.sample(safe_points[1:-1], num_chunks)
        split_indices.sort()
        
        chunks = []
        last_idx = 0
        for idx in split_indices:
            chunks.append(actions[last_idx:idx])
            last_idx = idx
        chunks.append(actions[last_idx:])
        
        last_func_name = None
        param_overrides = params if params else []
        param_tuple = [{"value": "{" + (p["value"] if p["value"].startswith("l!") else "l!" + p["value"]) + "}", "t": "any", "l": "any"} for p in param_overrides]
        
        for i in range(len(chunks) - 1, -1, -1):
            chunk = chunks[i]
            current_func_name = self.generate_random_name()
            func_actions = list(chunk)
            
            if last_func_name:
                chain_res_var = "l!" + self.generate_random_name()
                call_next = {
                    "id": "87",
                    "text": [
                        "Run function",
                        {"value": last_func_name, "t": "string", "l": "function"},
                        {"value": param_tuple, "t": "tuple"},
                        "→",
                        {"value": chain_res_var, "l": "variable?", "t": "string"}
                    ],
                    "globalid": self.generate_global_id()
                }
                if is_function:
                    return_next = {
                        "id": "115",
                        "text": ["Return", {"value": "{" + chain_res_var + "}", "t": "any", "l": "any"}],
                        "globalid": self.generate_global_id()
                    }
                    func_actions.append(call_next)
                    func_actions.append(return_next)
                else:
                    func_actions.append(call_next)
            
            script_content.append({
                "id": "6",
                "text": ["Define function", {"value": current_func_name, "t": "string", "l": "function"}],
                "variable_overrides": param_overrides,
                "actions": func_actions,
                "x": str(random.randint(2000, 8000)),
                "y": str(random.randint(2000, 8000)),
                "width": str(random.randint(300, 600)),
                "globalid": self.generate_global_id()
            })
            last_func_name = current_func_name

        final_actions = []
        final_res_var = "l!" + self.generate_random_name()
        call_chain = {
            "id": "87",
            "text": [
                "Run function",
                {"value": last_func_name, "t": "string", "l": "function"},
                {"value": param_tuple, "t": "tuple"},
                "→",
                {"value": final_res_var, "l": "variable?", "t": "string"}
            ],
            "globalid": self.generate_global_id()
        }
        final_actions.append(call_chain)
        if is_function:
            final_actions.append({
                "id": "115",
                "text": ["Return", {"value": "{" + final_res_var + "}", "t": "any", "l": "any"}],
                "globalid": self.generate_global_id()
            })
            
        return final_actions

    def create_math_library(self, script_content):
        ops = {"Increase": "12", "Decrease": "13", "Multiply": "14", "Divide": "15"}
        for op_name, op_id in ops.items():
            func_name = self.generate_random_name()
            self.math_funcs[op_name] = func_name
            lib_res = self.generate_random_name()
            lib_a = self.generate_random_name()
            lib_b = self.generate_random_name()
            
            actions = [
                {
                    "id": "11",
                    "text": ["Set", {"value": lib_res, "l": "variable", "t": "string"}, "to", {"value": "{l!" + lib_a + "}", "t": "any"}],
                    "globalid": self.generate_global_id()
                },
                {
                    "id": op_id,
                    "text": [op_name, {"value": lib_res, "l": "variable", "t": "string"}, "by", {"value": "{l!" + lib_b + "}", "t": "any"}],
                    "globalid": self.generate_global_id()
                },
                {
                    "id": "115",
                    "text": ["Return", {"value": "{" + lib_res + "}", "t": "any"}],
                    "globalid": self.generate_global_id()
                }
            ]
            script_content.append({
                "id": "6",
                "text": ["Define function", {"value": func_name, "t": "string", "l": "function"}],
                "variable_overrides": [{"value": lib_a}, {"value": lib_b}],
                "actions": actions,
                "x": str(random.randint(4000, 6000)),
                "y": str(random.randint(4000, 6000)),
                "width": "600",
                "globalid": self.generate_global_id()
            })

    def obfuscate_event(self, event, script_content):
        event["globalid"] = self.generate_global_id()
        if "text" in event:
            event["text"] = self.process_text_field(event["text"])
        
        overrides = []
        if "variable_overrides" in event:
            new_overrides = []
            for ov in event["variable_overrides"]:
                new_ov = ov.copy()
                new_ov["value"] = self.get_obfuscated_name(ov["value"])
                new_overrides.append(new_ov)
            event["variable_overrides"] = new_overrides
            overrides = new_overrides
            
        if "actions" in event:
            new_actions = [self.obfuscate_action(a) for a in event["actions"]]
            is_func = (str(event.get("id")) == "6")
            event["actions"] = self.split_actions(new_actions, script_content, params=overrides, is_function=is_func)
            
        return event

    def obfuscate_script(self, script_obj):
        if script_obj.get("class") != "script":
            return script_obj
        script_obj["globalid"] = self.generate_global_id()
        if "content" in script_obj:
            new_content = []
            self.create_math_library(new_content)
            for event in script_obj["content"]:
                new_content.append(self.obfuscate_event(event, new_content))
            script_obj["content"] = new_content
        return script_obj

    def obfuscate_children(self, children):
        new_children = []
        for child in children:
            new_children.append(self.obfuscate_element(child))
        return new_children

    def obfuscate_element(self, element):
        element["globalid"] = self.generate_global_id()
        
        if element.get("class") == "script":
            return self.obfuscate_script(element)
            
        if "children" in element:
            element["children"] = self.obfuscate_children(element["children"])
            
        return element

    def run(self, data):
        if not isinstance(data, list):
            raise ValueError("CatWeb JSON root must be an array.")
            
        obfuscated_data = []
        for element in data:
            obfuscated_data.append(self.obfuscate_element(element))
            
        return obfuscated_data

def main():
    parser = argparse.ArgumentParser(description="CatWeb Script Obfuscator")
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("-o", "--output", help="Output JSON file", default="obfuscated.json")
    
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        obfuscator = CatWebObfuscator()
        result = obfuscator.run(data)
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        print(f"Successfully obfuscated {args.input} -> {args.output}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
