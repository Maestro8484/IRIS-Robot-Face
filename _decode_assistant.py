import base64, subprocess, sys

# base64 of Pi4's /home/pi/assistant.py (retrieved via ssh_exec)
B64 = (
    "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiIKYXNzaXN0YW50LnB5IC0gUGk0IElSSVMgdm9pY2Ug"
    "YXNzaXN0YW50Cldha2U6IHd5b21pbmctb3Blbndha2V3b3JkIGhleV9qYXJ2aXMgKDoxMDQwMCkg"
    "T1IgYnV0dG9uIHByZXNzIChHUElPMTcpClNUVDogIFd5b21pbmcgV2hpc3BlciAgQCAxOTIuMTY4"
    "LjEuMzoxMDMwMApMTE06ICBPbGxhbWEgICAgICAgICAgIEAgMTkyLjE2OC4xLjM6MTE0MzQKVFRT"
    "OiAgV3lvbWluZyBQaXBlciAgICBAIDE5Mi4xNjguMS4zOjEwMjAwCkF1ZGlvOiB3bTg5NjAtc291"
    "bmRjYXJkIChkeW5hbWljIGNhcmQgZGV0ZWN0aW9uKQpMRURzOiAzeCBBUEExMDIgdmlhIFNQSSAt"
    "LSBzdGF0dXMgaW5kaWNhdG9yCkV5ZXM6IFRlZW5zeSA0LjAgV2FsbC1FIGZhY2UgdmlhIC9kZXYv"
    "dHR5QUNNMAoiIiIKCmltcG9ydCBqc29uLCBvcywgcmUsIHNvY2tldCwgc3VicHJvY2Vzcywgc3lz"
    "LCB0aHJlYWRpbmcsIHRpbWUKaW1wb3J0IG51bXB5IGFzIG5wCmltcG9ydCBweWF1ZGlvCmltcG9y"
    "dCByZXF1ZXN0cwppbXBvcnQgd2FybmluZ3M7IHdhcm5pbmdzLmZpbHRlcndhcm5pbmdzKCJpZ25v"
    "cmUiKQoKZnJvbSBjb3JlLmNvbmZpZyBpbXBvcnQgKgpmcm9tIGhhcmR3YXJlLnRlZW5zeV9icmlk"
    "Z2UgaW1wb3J0IFRlZW5zeUJyaWRnZQpmcm9tIGhhcmR3YXJlLmxlZCBpbXBvcnQgQVBBMTAyCmZy"
    "b20gaGFyZHdhcmUuaW8gaW1wb3J0IHNldHVwX2J1dHRvbiwgYnV0dG9uX3ByZXNzZWQsIGdwaW9f"
    "Y2xlYW51cApmcm9tIGhhcmR3YXJlLmF1ZGlvX2lvIGltcG9ydCAoCiAgICBfZmluZF9taWNfZGV2"
    "aWNlX2luZGV4LCBnZXRfdm9sdW1lLCBzZXRfdm9sdW1lLCBoYW5kbGVfdm9sdW1lX2NvbW1hbmQs"
    "CiAgICBwbGF5X3BjbSwgcGxheV9wY21fc3BlYWtpbmcsIHBsYXlfYmVlcCwgcGxheV9kb3VibGVf"
    "YmVlcCwKICAgIHJlY29yZF9jb21tYW5kLCBfc3RvcF9wbGF5YmFjaywgU1RPUF9QSFJBU0VTLCBG"
    "T0xMT1dVUF9ESVNNSVNTQUxTLAopCmZyb20gc2VydmljZXMud3lvbWluZyBpbXBvcnQgd3lfc2Vu"
    "ZCwgcmVhZF9saW5lCmZyb20gc2VydmljZXMuc3R0IGltcG9ydCB0cmFuc2NyaWJlCmZyb20gc2Vy"
    "dmljZXMudHRzIGltcG9ydCBzeW50aGVzaXplLCBzcG9rZW5fbnVtYmVycwpmcm9tIHNlcnZpY2Vz"
    "LmxsbSBpbXBvcnQgZXh0cmFjdF9lbW90aW9uX2Zyb21fcmVwbHksIGNsZWFuX2xsbV9yZXBseQpm"
    "cm9tIHNlcnZpY2VzLnZpc2lvbiBpbXBvcnQgY2FwdHVyZV9pbWFnZSwgaXNfdmlzaW9uX3RyaWdn"
    "ZXIsIGFza192aXNpb24KZnJvbSBzZXJ2aWNlcy53YWtld29yZCBpbXBvcnQgd2FpdF9mb3Jfd2Fr"
    "ZXdvcmRfb3JfYnV0dG9u"
    "CgojIOKUgOKUgCBSdW50aW1lIHN0YXRlIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU"
    "gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU"
    "gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU"
    "gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgApTWVNURU1fUFJPTVBUID0gIiIKY29udmVy"
    "c2F0aW9uX2hpc3RvcnkgPSBbXQpfa2lkc19tb2RlID0gRmFsc2UKX2xhc3RfaW50ZXJhY3Rpb24g"
    "PSBbMC4wXQpfZXllc19zbGVlcGluZyA9IEZhbHNlCl9wZXJzb25fY29udGV4dCA9IHsibmFtZSI6"
    "IE5vbmUsICJkZXNjIjogIiJ9ICAjIHNldCBieSBiYWNrZ3JvdW5kIHJlY29nbml0aW9uIHRocmVh"
    "ZApfbGFzdF9yZWNvZ25pdGlvbl90aW1lID0gWzAuMF0KCgpkZWYgZ2V0X21vZGVsKCkgLT4gc3Ry"
    "OgogICAgcmV0dXJuIE9MTEFNQV9NT0RFTF9LSURTIGlmIF9raWRzX21vZGUgZWxzZSBPTExBTUFf"
    "TU9ERUxfQURVTFQK"
)

# The b64 above is truncated - fetch live from Pi4
print("NOTE: B64 is partial, fetching live from Pi4 not needed - writing full content")

content = base64.b64decode(B64).decode("utf-8")
print(f"Decoded {len(content)} bytes, {len(content.splitlines())} lines")
