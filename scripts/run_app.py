#!/usr/bin/env python3
"""Launch the LIRelay desktop GUI."""

from src.gui_app import LIRelayApp


def main() -> None:
    app = LIRelayApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
