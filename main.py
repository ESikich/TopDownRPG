# main.py
#!/usr/bin/env python3
"""Entry point for the ECS Dungeon Crawler"""
import sys
from core.app import App

def main():
    app = App()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()