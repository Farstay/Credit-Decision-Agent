from app.services.rag import index_rules

if __name__ == "__main__":
    count = index_rules()
    print(f"Проиндексировано правил: {count}")