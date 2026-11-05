@external("cms", "read_content")
declare function readContent(): i32;

export function run(): i32 {
  return readContent() + 1;
}
