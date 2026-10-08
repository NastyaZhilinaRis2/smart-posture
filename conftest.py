# Prompt: "Помоги настроить pytest так, чтобы он видел модуль main из корня проекта"
# Prompt: "Добавь корень проекта в sys.path"

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))