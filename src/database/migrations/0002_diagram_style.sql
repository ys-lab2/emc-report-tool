-- 構成図の色カスタマイズ（塗りつぶし色・線色）に対応するためのカラム追加。
-- NULLの場合はアプリのデフォルト色を使用する。

ALTER TABLE diagram_nodes ADD COLUMN fill_color TEXT;
ALTER TABLE diagram_nodes ADD COLUMN stroke_color TEXT;
ALTER TABLE diagram_edges ADD COLUMN line_color TEXT;
