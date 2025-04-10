
#!/usr/bin/env python3
"""Script per testare il parser markdown."""
import argparse
import logging
from src.tools import MarkdownParserTool

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Testa il parser markdown con vari input."""
    parser = argparse.ArgumentParser(description="Test del parser markdown")
    parser.add_argument("--file", required=True, help="Path del file markdown")
    parser.add_argument("--section", default=None, help="Sezione da cercare (opzionale)")
    
    args = parser.parse_args()
    
    try:
        # Inizializza il tool
        markdown_tool = MarkdownParserTool(file_path=args.file)
        
        # Ottieni il contenuto
        print("\n" + "="*80)
        print(f"Test del parser markdown sul file: {args.file}")
        print(f"Cercando la sezione: {args.section if args.section else 'intero documento'}")
        print("="*80 + "\n")
        
        content = markdown_tool.get_content(args.section)
        
        print("\n" + "="*80)
        print("RISULTATO:")
        print("="*80)
        print(content)
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"Errore durante il test: {str(e)}")

if __name__ == "__main__":
    main()
