from flowlane_api.common import new_id, utcnow
from flowlane_api.errors import NotFoundError
from flowlane_api.models import TaskRecord
from flowlane_api.repositories import Store
from flowlane_api.schemas import CreateTaskInput, MoveTaskInput, Task, UpdateTaskInput


class TaskService:
    def __init__(self, store: Store) -> None:
        self._store = store

    def create_task(self, column_id: str, data: CreateTaskInput) -> Task:
        self._require_column(column_id)
        timestamp = utcnow()
        task = TaskRecord(
            id=new_id("task"),
            column_id=column_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            # Appended at the end: position = current task count in the column.
            position=len(self._store.tasks.list_for_column(column_id)),
            due_date=data.due_date,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self._store.tasks.add(task)
        return Task.model_validate(task)

    def get_task(self, task_id: str) -> Task:
        return Task.model_validate(self._require_task(task_id))

    def update_task(self, task_id: str, data: UpdateTaskInput) -> Task:
        task = self._require_task(task_id)
        # Only fields the client actually sent are applied (`dueDate: null` clears it,
        # an omitted `dueDate` leaves it alone).
        changes = data.model_dump(exclude_unset=True)

        target_column_id = changes.pop("column_id", None)
        if target_column_id is not None and target_column_id != task.column_id:
            self._require_column(target_column_id)
            source_column_id = task.column_id
            # Count the destination before re-pointing the task, or it counts itself.
            task.position = len(self._store.tasks.list_for_column(target_column_id))
            task.column_id = target_column_id
            self._reindex_column(source_column_id)

        for field, value in changes.items():
            setattr(task, field, value)
        task.updated_at = utcnow()
        self._store.tasks.save(task)
        return Task.model_validate(task)

    def delete_task(self, task_id: str) -> None:
        task = self._require_task(task_id)
        self._store.tasks.delete(task.id)
        self._reindex_column(task.column_id)

    def move_task(self, task_id: str, data: MoveTaskInput) -> Task:
        task = self._require_task(task_id)
        self._require_column(data.column_id)
        source_column_id = task.column_id

        # Build the destination's post-move order: everything already there (minus
        # this task, for same-column moves), with the task spliced in at the
        # requested index, clamped to [0, len].
        destination = [
            t for t in self._store.tasks.list_for_column(data.column_id) if t.id != task.id
        ]
        index = max(0, min(data.position, len(destination)))
        destination.insert(index, task)

        task.column_id = data.column_id
        task.updated_at = utcnow()
        for position, sibling in enumerate(destination):
            if sibling.position != position or sibling is task:
                sibling.position = position
                self._store.tasks.save(sibling)

        if source_column_id != data.column_id:
            self._reindex_column(source_column_id)
        return Task.model_validate(task)

    def _reindex_column(self, column_id: str) -> None:
        """Make the column's task positions contiguous (0, 1, 2, …) in their current order."""
        for position, task in enumerate(self._store.tasks.list_for_column(column_id)):
            if task.position != position:
                task.position = position
                self._store.tasks.save(task)

    def _require_task(self, task_id: str) -> TaskRecord:
        task = self._store.tasks.get(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        return task

    def _require_column(self, column_id: str) -> None:
        if self._store.columns.get(column_id) is None:
            raise NotFoundError("Column not found")
