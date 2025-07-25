import json
import os
import sys
from typing import Optional, Dict, List

class ModelListManager:
    def __init__(self):
        """Initialize with default settings"""
        self.model_list_file = "model_list.json"
        self.model_list = {"LLM": []}
        
        if os.path.exists(self.model_list_file):
            with open(self.model_list_file, "r", encoding="utf-8") as f:
                self.model_list = json.load(f)
    
    def _save_model_list(self):
        """Save current state to model_list.json"""
        with open(self.model_list_file, "w", encoding="utf-8") as f:
            json.dump(self.model_list, f, indent=4, ensure_ascii=False)
    
    def _find_model_index(self, model_name: str) -> Optional[int]:
        """Find model index by exact name match (case sensitive)"""
        for i, model in enumerate(self.model_list["LLM"]):
            if model["name"] == model_name:
                return i
        return None
    
    def add_model(self, json_filename: str) -> bool:
        """Add model from JSON file in current directory"""
        try:
            with open(json_filename, "r", encoding="utf-8") as f:
                model_data = json.load(f)
            
            if self._find_model_index(model_data["name"]) is not None:
                print(f"Model '{model_data['name']}' already exists")
                return False
            
            self.model_list["LLM"].append(model_data)
            self._save_model_list()
            print(f"Model '{model_data['name']}' added successfully")
            return True
        except FileNotFoundError:
            print(f"Error: File '{json_filename}' not found")
            return False
        except Exception as e:
            print(f"Error adding model: {str(e)}")
            return False
    
    def delete_model(self, model_name: str) -> bool:
        """Delete model by exact name match"""
        index = self._find_model_index(model_name)
        if index is None:
            print(f"Model '{model_name}' not found")
            return False
        
        self.model_list["LLM"].pop(index)
        self._save_model_list()
        print(f"Model '{model_name}' deleted successfully")
        return True
    
    def update_model(self, json_filename: str) -> bool:
        """Update model from JSON file in current directory"""
        try:
            with open(json_filename, "r", encoding="utf-8") as f:
                new_data = json.load(f)
            
            index = self._find_model_index(new_data["name"])
            if index is None:
                print(f"Model '{new_data['name']}' not found (use add_model instead)")
                return False
            
            self.model_list["LLM"][index] = new_data
            self._save_model_list()
            print(f"Model '{new_data['name']}' updated successfully")
            return True
        except Exception as e:
            print(f"Error updating model: {str(e)}")
            return False


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 3:
        print("Usage:")
        print("  python Gen_final_model_list.py add <json_filename>")
        print("  python Gen_final_model_list.py update <json_filename>")
        print("  python Gen_final_model_list.py delete <model_name>")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    manager = ModelListManager()
    
    if command == "add":
        json_filename = sys.argv[2]
        if not json_filename.endswith('.json'):
            print(f"Error: '{json_filename}' must be a .json file")
            sys.exit(1)
        manager.add_model(json_filename)
    elif command == "update":
        json_filename = sys.argv[2]
        if not json_filename.endswith('.json'):
            print(f"Error: '{json_filename}' must be a .json file")
            sys.exit(1)
        manager.update_model(json_filename)
    elif command == "delete":
        model_name = sys.argv[2]
        manager.delete_model(model_name)
    else:
        print(f"Unknown command: {command}")
        print("Available commands: add, update, delete")
        sys.exit(1)

if __name__ == "__main__":
    main()