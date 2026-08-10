from dxgi_gpu_enum import enumerate_gpus


def main() -> None:
    for number, gpu in enumerate(enumerate_gpus()):
        print(f"GPU {number}: {gpu.name}")


if __name__ == "__main__":
    main()
