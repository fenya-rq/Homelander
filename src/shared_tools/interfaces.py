from src.storage.repositories import RepositoryContainer


class BaseManagerInterface:

    def __init__(self, repos: RepositoryContainer):
        self.repos = repos
