#!/usr/bin/env python3
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from McElieceCipher.mceliece.mceliece import McEliece

def generate_keys():
    print(" Generating McEliece mock keys (mock secure)...\n")

    try:
        mc = McEliece()
        public, private = mc.generate_keys()

        mc.save_keys("private.key", "public.key")

        print(" Keys saved successfully!")
        print(f" Public key:  {os.path.abspath('public.key')}")
        print(f" Private key: {os.path.abspath('private.key')}")

    except Exception as e:
        print(f"\n Error: Key generation failed\n{str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # Confirm overwrite if files already exist
    if os.path.exists("private.key") or os.path.exists("public.key"):
        print("  Key files already exist.")
        confirm = input("❓ Overwrite them? [y/N]: ").strip().lower()
        if confirm != "y":
            print(" Aborted.")
            sys.exit(0)
        if os.path.exists("private.key"):
            os.remove("private.key")
        if os.path.exists("public.key"):
            os.remove("public.key")

    generate_keys()
