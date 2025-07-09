from pathlib import Path
import sys
import json


class CovReport:
    """
    Class for a .covreport file.
    """

    def __init__(self, branches: dict = {}):
        """
        Initialize an empty CovReport or with given branches.
        """
        self.branches = branches

    @classmethod
    def from_file(cls, file_path: Path):
        """
        Class method to create a CovReport instance from a file path.

        :param file_path: Path to the .covreport file.
        :return: An instance of CovReport.
        """
        instance = cls()

        with open(file_path, "r") as file:
            lines = file.readlines()
        current_function = "start"
        for line in lines:
            line = line.rstrip()
            if len(line) > 1 and not line[0].isspace() and line.endswith(":"):
                # this is a file/function idicator
                current_function = line.strip()
            elif "Branch (" in line and "True:" in line and "False:" in line:
                # this is a branch coverage line, like:
                #   |  Branch (15:9): [True: 0, False: 1]
                loc = line.split("(")[-1].split(")")[0].strip()
                into_true = line.split("True:")[-1].split(",")[0].strip()
                into_false = line.split("False:")[-1].split("]")[0].strip()

                branch_id = current_function + loc
                into_true = into_true != "0"
                into_false = into_false != "0"
                instance.branches[branch_id] = (into_true, into_false)

        return instance

    def merge(self, other: "CovReport"):
        """
        Merge another CovReport into this one.

        :param other: Another CovReport instance to merge.
        """
        for branch_id, (into_true, into_false) in other.branches.items():
            if branch_id in self.branches:
                existing_true, existing_false = self.branches[branch_id]
                self.branches[branch_id] = (
                    existing_true or into_true,
                    existing_false or into_false,
                )
            else:
                self.branches[branch_id] = (into_true, into_false)

    @property
    def branch_covered(self):
        """
        The branch covered count.
        """
        count = 0
        for into_true, into_false in self.branches.values():
            if into_true:
                count += 1
            if into_false:
                count += 1
        return count

    def save(self, file_path: Path):
        """
        Save the CovReport to a file.

        :param file_path: Path to save the .covreport file.
        """
        with open(file_path, "w") as file:
            json.dump(
                {
                    "branch_covered": self.branch_covered,
                    "branches": {
                        branch_id: {"into_true": into_true, "into_false": into_false}
                        for branch_id, (into_true, into_false) in self.branches.items()
                    },
                },
                file,
                indent=4,
            )


def main():
    if len(sys.argv) < 3:
        print(
            f"Usage: {sys.argv[0]} <result_directory> <library_name>\n"
            f"For example: {sys.argv[0]} oss-fuzz-gen/results pugixml"
        )
        sys.exit(1)
    result_directory = Path(sys.argv[1])
    library_name = sys.argv[2]

    cov_report = CovReport()

    for output_dir in result_directory.iterdir():
        if output_dir.name.startswith(f"output-{library_name}-"):
            report_dir = output_dir / "code-coverage-reports"
            if not report_dir.exists():
                print(f"[Warning] Directory {report_dir} does not exist, skipping.")
                continue
            for covreport_file in report_dir.rglob("*.covreport"):
                cov_report.merge(CovReport.from_file(covreport_file))
                print(f"[Success] Processed {covreport_file}")

    if not cov_report.branches:
        print(f"[Warning] No branches found in the coverage reports.")
        sys.exit(1)

    output_file = result_directory / f"{library_name}.json"
    cov_report.save(output_file)
    print(f"[Success] Merged coverage report saved to {output_file}")
    print(f"[Info] Total branches covered: {cov_report.branch_covered}")


if __name__ == "__main__":
    main()
