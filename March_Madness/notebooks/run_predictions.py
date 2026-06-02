"""
Tiny CLI-style entrypoint so you can run:

    python -m March_Madness.notebooks.run_predictions

It simply calls the existing Winky.main pipeline.
"""

from March_Madness.Winky import main


if __name__ == "__main__":
    main()

