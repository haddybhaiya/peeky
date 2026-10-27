# Good smoke fixture

One opt-in command runs an actual Python script in the selected sandbox.

```bash peeky
python smoke.py
```

An unannotated block is deliberately ignored:

```bash
python -c "print('do not run unannotated commands')"
```
