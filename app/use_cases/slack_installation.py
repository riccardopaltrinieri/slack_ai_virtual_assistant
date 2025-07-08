import logging
from logging import Logger
from typing import Optional
from uuid import uuid4

from google.cloud.firestore import Client
from slack_sdk.oauth import InstallationStore, OAuthStateStore
from slack_sdk.oauth.installation_store import Bot, Installation


class FirestoreSlackInstallationStore(InstallationStore):
    datastore_client: Client

    def __init__(
        self,
        *,
        datastore_client: Client,
        logger: Logger,
    ):
        self.datastore_client = datastore_client
        self._logger = logger

    @property
    def logger(self) -> Logger:
        if self._logger is None:
            self._logger = logging.getLogger(__name__)
        return self._logger

    @staticmethod
    def installation_key(
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str],
        suffix: Optional[str] = None,
        is_enterprise_install: Optional[bool] = None,
    ):
        enterprise_id = enterprise_id or "none"
        team_id = "none" if is_enterprise_install else team_id or "none"
        name = f"{enterprise_id}-{team_id}-{user_id}" if user_id else f"{enterprise_id}-{team_id}"
        if suffix is not None:
            name += "-" + suffix
        return name

    @staticmethod
    def bot_key(
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        suffix: Optional[str] = None,
        is_enterprise_install: Optional[bool] = None,
    ):
        enterprise_id = enterprise_id or "none"
        team_id = "none" if is_enterprise_install else team_id or "none"
        name = f"{enterprise_id}-{team_id}"
        if suffix is not None:
            name += "-" + suffix
        return name

    def save(self, i: Installation):
        # the latest installation in the workspace
        doc_ref = self.datastore_client.collection("installations").document(
            self.installation_key(
                enterprise_id=i.enterprise_id,
                team_id=i.team_id,
                user_id=None,  # user_id is removed
                is_enterprise_install=i.is_enterprise_install,
            )
        )
        doc_ref.set(i.to_dict())

        # the latest installation associated with a user
        doc_ref = self.datastore_client.collection("installations").document(
            self.installation_key(
                enterprise_id=i.enterprise_id,
                team_id=i.team_id,
                user_id=i.user_id,
                is_enterprise_install=i.is_enterprise_install,
            )
        )
        doc_ref.set(i.to_dict())

        # history data
        doc_ref = self.datastore_client.collection("installations").document(
            self.installation_key(
                enterprise_id=i.enterprise_id,
                team_id=i.team_id,
                user_id=i.user_id,
                is_enterprise_install=i.is_enterprise_install,
                suffix=str(i.installed_at),
            )
        )
        doc_ref.set(i.to_dict())

        # the latest bot authorization in the workspace
        bot = i.to_bot()
        doc_ref = self.datastore_client.collection("bots").document(
            self.bot_key(
                enterprise_id=i.enterprise_id,
                team_id=i.team_id,
                is_enterprise_install=i.is_enterprise_install,
            )
        )
        doc_ref.set(bot.to_dict())

        # history data
        doc_ref = self.datastore_client.collection("bots").document(
            self.bot_key(
                enterprise_id=i.enterprise_id,
                team_id=i.team_id,
                is_enterprise_install=i.is_enterprise_install,
                suffix=str(i.installed_at),
            )
        )
        doc_ref.set(bot.to_dict())

    def find_bot(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Bot]:
        doc = (
            self.datastore_client.collection("bots")
            .document(
                self.bot_key(
                    enterprise_id=enterprise_id,
                    team_id=team_id,
                    is_enterprise_install=is_enterprise_install,
                )
            )
            .get()
        )
        entity = doc.to_dict() if doc.exists else None
        if entity is not None:
            entity["installed_at"] = entity["installed_at"].timestamp()
            return Bot(**entity)
        return None

    def find_installation(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
        is_enterprise_install: Optional[bool] = False,
    ) -> Optional[Installation]:
        doc = (
            self.datastore_client.collection("installations")
            .document(
                self.installation_key(
                    enterprise_id=enterprise_id,
                    team_id=team_id,
                    user_id=user_id,
                    is_enterprise_install=is_enterprise_install,
                )
            )
            .get()
        )
        entity = doc.to_dict() if doc.exists else None
        if entity is not None:
            entity["installed_at"] = entity["installed_at"].timestamp()
            return Installation(**entity)
        return None

    def delete_installation(
        self,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        user_id: Optional[str] = None,
    ) -> None:
        prefix = self.installation_key(
            enterprise_id=enterprise_id,
            team_id=team_id,
            user_id=user_id,
        )
        installations_ref = self.datastore_client.collection("installations")
        query = installations_ref.where("__name__", ">=", prefix).where("__name__", "<", prefix + "\uf8ff")
        for doc in query.stream():
            if doc.id.startswith(prefix):
                doc.reference.delete()
            else:
                break

    def delete_bot(
        self,
        enterprise_id: Optional[str],
        team_id: Optional[str],
    ) -> None:
        prefix = self.bot_key(
            enterprise_id=enterprise_id,
            team_id=team_id,
        )
        bots_ref = self.datastore_client.collection("bots")
        query = bots_ref.where("__name__", ">=", prefix).where("__name__", "<", prefix + "\uf8ff")
        for doc in query.stream():
            if doc.id.startswith(prefix):
                doc.reference.delete()
            else:
                break

    def delete_all(
        self,
        enterprise_id: Optional[str],
        team_id: Optional[str],
    ):
        self.delete_bot(enterprise_id=enterprise_id, team_id=team_id)
        self.delete_installation(enterprise_id=enterprise_id, team_id=team_id, user_id=None)


class FirestoreSlackOAuthStateStore(OAuthStateStore):
    logger: Logger
    datastore_client: Client
    collection_id: str

    def __init__(
        self,
        *,
        datastore_client: Client,
        logger: Logger,
    ):
        self.datastore_client = datastore_client
        self._logger = logger
        self.collection_id = "oauth_state_values"

    @property
    def logger(self) -> Logger:
        if self._logger is None:
            self._logger = logging.getLogger(__name__)
        return self._logger

    def consume(self, state: str) -> bool:
        doc_ref = self.datastore_client.collection(self.collection_id).document(state)
        if doc_ref.get().exists:
            doc_ref.delete()
            return True
        return False

    def issue(self, *args, **kwargs) -> str:
        state_value = str(uuid4())
        doc_ref = self.datastore_client.collection(self.collection_id).document(state_value)
        doc_ref.set({"value": state_value})
        return state_value
