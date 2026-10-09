class FakeFileStorage:
    def __init__(self):
        self.saved_files = {}

    def create_path(self, filename: str):
        return filename

    async def save_stream(
        self,
        file,
        destination,
        max_size: int,
    ) -> int:
        content = await file.read()

        if len(content) > max_size:
            raise ValueError("File too large")

        self.saved_files[str(destination)] = content

        return len(content)