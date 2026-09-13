import gc

import pytest


@pytest.fixture(autouse=True)
def _cleanup_com_objects_between_tests():
    """Word COMオブジェクトの解放（pywin32ラッパーの__del__）がPythonのGCタイミングに
    依存するため、次のテストのWordセッション実行中に遅延解放が発生して低レベルの
    COM例外ログが出ることがある。テスト境界で明示的にGCしてCOM解放を確定させ、
    次のテストへ持ち越さないようにする。"""
    yield
    gc.collect()
