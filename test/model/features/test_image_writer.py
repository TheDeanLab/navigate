import pytest


@pytest.fixture()
def image_writer(dummy_model):
    from aslm.model.features.image_writer import ImageWriter

    model = dummy_model
    model.configuration["experiment"]["Saving"]["save_directory"] = "test_save_dir"

    writer = ImageWriter(dummy_model)

    yield writer

    writer.close()


def test_generate_metadata(image_writer):
    assert image_writer.generate_meta_data()


def test_image_write(image_writer):
    from numpy.random import rand

    # Randomize the data buffer
    for i in range(image_writer.model.data_buffer.shape[0]):
        image_writer.model.data_buffer[i, ...] = rand(
            image_writer.model.img_width, image_writer.model.img_height
        )

    image_writer.save_image(list(range(image_writer.model.number_of_frames)))

    delete_folder("test_save_dir")


def delete_folder(dir):
    import os

    bn = os.path.basename(dir)
    if bn == "." or bn == "..":
        raise OSError("Cannot delete the directory '{dir}'.")

    for cand in os.listdir(dir):
        cp = os.path.join(dir, cand)
        if os.path.isdir(cp):
            delete_folder(cp)
        elif os.path.isfile(cp):
            try:
                os.remove(cp)
            except PermissionError:
                # Windows permission error, file is still open somehow
                pass
        else:
            raise TypeError(f"Unknown entity {cand} cannot be deleted. Aborting.")

    os.rmdir(dir)
