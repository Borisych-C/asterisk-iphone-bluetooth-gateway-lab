"""Exercise upstream mbl_read with a single partial frame on a local socket."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("chan_mobile", type=Path, help="stock addons/chan_mobile.c from the release to test")
args = parser.parse_args()
work = Path(__file__).resolve().parent
source = args.chan_mobile.read_text()
start = source.index("static struct ast_frame *mbl_read(struct ast_channel *ast)\n{")
callback = source[start:source.index("\n}\n", start) + 3]
sizes = {}
for name in ("DEVICE_FRAME_SIZE", "CHANNEL_FRAME_SIZE"):
    sizes[name] = int(re.search(rf"(?m)^#define {name}\s+(\d+)", source)[1])
if not 0 < sizes["DEVICE_FRAME_SIZE"] < sizes["CHANNEL_FRAME_SIZE"] <= 320:
    parser.error("the fixture requires a partial device frame and a channel frame of at most 320 bytes")

# Use the same model Asterisk frame and smoother as the corrected-module test.
fixture = (work / "test.c").read_text().split("static int option_error;", 1)[0]
fixture = fixture.replace("#define CHANNEL_FRAME_SIZE 320",
                          "\n".join(f"#define {name} {size}" for name, size in sizes.items()))
main = r"""
int main(void)
{
    int sockets[2];
    assert(socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_NONBLOCK, 0, sockets) == 0);
    struct ast_smoother input = { .size = CHANNEL_FRAME_SIZE };
    struct mbl_pvt p = { .owner = &p, .sco_socket = sockets[0], .bt_in_smoother = &input };
    struct ast_channel channel = { .pvt = &p };
    unsigned char pcm[DEVICE_FRAME_SIZE] = {0};
    assert(send(sockets[1], pcm, sizeof(pcm), 0) == sizeof(pcm));
    struct ast_frame *result = mbl_read(&channel);
    assert(input.used == sizeof(pcm) && (errno == EAGAIN || errno == EWOULDBLOCK));
    printf("frame=%s remainder=%u errno=%d\n",
           result == NULL ? "NULL" : result == &ast_null_frame ? "ast_null_frame" : "other",
           input.used, errno);
    close(sockets[0]);
    close(sockets[1]);
    return result == &ast_null_frame ? 0 : 1;
}
"""
with tempfile.TemporaryDirectory() as folder:
    program = Path(folder) / "check.c"
    binary = Path(folder) / "check"
    program.write_text(fixture + callback + main)
    subprocess.run(["cc", "-Wall", "-Werror", "-Wno-unused-function", "-O1", "-g",
                    "-fsanitize=address,undefined", "-I" + str(work / "input/include-bluetooth"),
                    str(program), "-o", str(binary)], check=True)
    raise SystemExit(subprocess.run([str(binary)], timeout=5).returncode)
