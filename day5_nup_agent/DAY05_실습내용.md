- ipykernel 설치
```
uv add ipykernel
```

- jupyter kernel에 등록
```
uv run python -m ipykernel install --user \
    --name .venv \
    --display-name "Python (rngd-lab)"
```
- vscode에서 확장프로그램 설치
![alt text](images/image.png)