# Stack V1 — hai bản thử có thể chạy lại

Đọc [đánh giá stack](../../docs/06_V1_TECH_STACK_EVALUATION.md) để biết phạm vi và kết quả. Bản thử chạy cục bộ với dữ liệu mẫu, giữ trạng thái builder trong bộ nhớ. Chỉ dùng ZIP mẫu và chạy trên localhost.

Từ thư mục gốc repo trong PowerShell:

```powershell
$spikeEnv = Join-Path $env:TEMP 'opendash-stack-v1'
python -m venv $spikeEnv
$spikePython = Join-Path $spikeEnv 'Scripts\python.exe'
& $spikePython -m pip install --only-binary=:all: -r spikes/stack-v1/requirements.txt
& $spikePython spikes/stack-v1/check.py -v
$themeZip = Join-Path $spikeEnv 'sample-theme.zip'
& $spikePython spikes/stack-v1/check.py --theme $themeZip
& $spikePython spikes/stack-v1/spike.py --serve 18765
```

Mở [builder localhost](http://127.0.0.1:18765/builder), chọn file sample-theme.zip, nhập Tiêu đề và Mô tả, bấm Xem trước rồi Lưu. Kiểm tra Trang công khai trước và sau khi lưu. Ctrl+C để dừng server.

Có thể thử thêm đường build plugin AssemblyScript trong terminal khác có Node/npm, với các biến spikeEnv và spikePython như trên:

```powershell
$guestWasm = Join-Path $spikeEnv 'guest.wasm'
npx.cmd --yes --package=assemblyscript@0.28.20 asc 'spikes/stack-v1/guest.ts' --outFile $guestWasm --runtime stub --optimize
& $spikePython spikes/stack-v1/check.py --guest $guestWasm
```
