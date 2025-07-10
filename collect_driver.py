from pathlib import Path
import shutil
import click


@click.command()
@click.option(
    "-r",
    "--result-dir",
    "res_dir",
    type=click.Path(path_type=Path, resolve_path=True, exists=True, dir_okay=True),
    help="The directory containing the OSS-Fuzz-Gen results.",
    required=True,
)
@click.option(
    "-o",
    "--output-dir",
    "out_dir",
    type=click.Path(path_type=Path, resolve_path=True, exists=True, dir_okay=True),
    help="The directory to output the fuzz drivers.",
    required=True,
)
@click.option(
    "-t",
    "--target",
    "target",
    type=str,
    help="The target name to filter the fuzz drivers.",
    required=True,
)
def collect_fuzz_drivers(res_dir: Path, out_dir: Path, target: str):
    source_files = []
    idx = 1
    for _dir in res_dir.glob(f"output-{target}-*"):
        driver_dir = _dir / "fuzz_targets"
        if not driver_dir.exists():
            print(f"Warning: {driver_dir} does not exist, skipping.")
            continue
        for driver_path in driver_dir.glob("*.fuzz_target"):
            if driver_path.is_file():
                # print(f"Found fuzz target: {driver_path}")
                source_files.append(driver_path)
                dst_file = out_dir / f"fuzz_driver_{idx}.cpp"
                idx += 1
                shutil.copy(driver_path, dst_file)
    print(f"Collected {len(source_files)} fuzz drivers for target '{target}' from {res_dir}.")

if __name__ == "__main__":
    collect_fuzz_drivers()