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


def delete_folder(top):
    # https://docs.python.org/3/library/os.html#os.walk
    # Delete everything reachable from the directory named in "top",
    # assuming there are no symbolic links.
    # CAUTION:  This is dangerous!  For example, if top == '/', it
    # could delete all your disk files.
    import os

    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            try:
                os.remove(os.path.join(root, name))
            except PermissionError:
                # Windows locks these files sometimes
                pass
        for name in dirs:
            os.rmdir(os.path.join(root, name))
