import pytest

from officeworld.generator.cell_type import CellType
from officeworld.generator.office_building import OfficeBuilding
from officeworld.generator.office_generator import OfficeGenerator
from officeworld.utils.serialisation import OfficeBuildingJSONHandler


@pytest.fixture
def sample_office_building():
    office_gen = OfficeGenerator(num_floors=10, elevator_location=(7, 7))
    office_building = office_gen.generate_office_building()
    return office_building


def test_office_building_serialization(tmp_path, sample_office_building):
    # Create a temporary file path
    file_path = tmp_path / "office_building_test.json"

    # Save the OfficeBuilding instance to the JSON file
    OfficeBuildingJSONHandler.save_to_json(sample_office_building, file_path)

    # Load the OfficeBuilding instance back from the JSON file
    loaded_office_building = OfficeBuildingJSONHandler.load_from_json(file_path)

    # Ensure that the layout, halls, and rooms are the same
    assert loaded_office_building.layout == sample_office_building.layout
    assert loaded_office_building.halls == sample_office_building.halls
    assert loaded_office_building.rooms == sample_office_building.rooms


if __name__ == "__main__":
    pytest.main([__file__])
