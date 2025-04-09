"""Script per riorganizzare la struttura del progetto TextGenerator."""
import os
import shutil
import sys

def reorganize_project():
    """Riorganizza la struttura del progetto per evitare duplicazioni."""
    # Directory di base
    base_dir = "/Users/davidescantamburlo/Desktop/TextGenerator"
    target_dir = os.path.join(base_dir, "content-generation-system", "src")
    
    # Assicurati che la directory di destinazione esista
    os.makedirs(target_dir, exist_ok=True)
    
    # Lista dei file Python nella directory principale che dovrebbero essere spostati
    files_to_move = [
        "tools.py",
        "tasks.py",
        "agents.py",
        "utils.py",
        "quality.py",
        "config_manager.py"
    ]
    
    # Sposta i file se esistono nella directory principale
    for file in files_to_move:
        source_path = os.path.join(base_dir, file)
        target_path = os.path.join(target_dir, file)
        
        if os.path.exists(source_path):
            # Controlla se esiste già un file con lo stesso nome nella destinazione
            if os.path.exists(target_path):
                print(f"ATTENZIONE: {file} esiste sia nella directory principale che in src/")
                choice = input(f"Vuoi sovrascrivere il file in src/ con quello della directory principale? (s/n): ")
                if choice.lower() != 's':
                    print(f"Mantengo entrambi i file. Rinomino quello nella directory principale in {file}.bak")
                    shutil.copy(source_path, source_path + ".bak")
                    continue
            
            # Sposta il file
            shutil.move(source_path, target_path)
            print(f"Spostato {file} nella directory src/")
    
    # Aggiorna il file main.py per utilizzare i percorsi corretti
    main_path = os.path.join(base_dir, "content-generation-system", "main.py")
    if os.path.exists(main_path):
        with open(main_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Aggiorna gli import
        content = content.replace("from tools", "from src.tools")
        content = content.replace("from tasks", "from src.tasks")
        content = content.replace("from agents", "from src.agents")
        content = content.replace("from utils", "from src.utils")
        content = content.replace("from quality", "from src.quality")
        content = content.replace("from config_manager", "from src.config_manager")
        
        with open(main_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Aggiornato main.py con i percorsi corretti")
    
    print("\nRiorganizzazione completata!")
    print("\nSuggerimenti:")
    print("1. Assicurati che tutti gli import nei file siano corretti")
    print("2. Esegui sempre lo script dalla directory content-generation-system")
    print("3. Usa percorsi relativi per i file di riferimento e output")

if __name__ == "__main__":
    print("Questo script riorganizzerà la struttura del progetto TextGenerator.")
    print("Sposterà i file Python dalla directory principale alla directory src/")
    choice = input("Vuoi continuare? (s/n): ")
    
    if choice.lower() == 's':
        reorganize_project()
    else:
        print("Operazione annullata.")