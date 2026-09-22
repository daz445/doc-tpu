try:
    from .cli import main
except ImportError:
    from doc_tpu.cli import main

if __name__ == "__main__":
    main()
