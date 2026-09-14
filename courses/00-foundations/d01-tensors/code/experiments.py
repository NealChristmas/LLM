"""D01: fixed CPU examples; no training or external data."""
import argparse
import platform
import torch


def show(name, value):
    print(f"{name}: shape={list(value.shape)}, dtype={value.dtype}, device={value.device}")
    print(value.tolist())


def experiment_a():
    for name, values in [("scalar", 7.0), ("vector", [1., 2.]),
                         ("X", [[1., 2.], [3., 4.], [5., 6.]]),
                         ("X_extended", [[1., 2.], [3., 4.], [5., 6.], [7., 8.]])]:
        show(name, torch.tensor(values, dtype=torch.float32, device="cpu"))


def experiment_b(first_weight=2.0):
    x = torch.tensor([[1., 2.], [3., 4.], [5., 6.]])
    w = torch.tensor([[first_weight], [3.]])
    b = torch.tensor([1.])
    show("X", x)
    show("W", w)
    show("b", b)
    y = x @ w + b
    show("Y = X @ W + b", y)
    print("parameter_count:", w.numel() + b.numel())
    print("forward_repeated_same_result:", torch.equal(y, x @ w + b))

    a = torch.tensor([[1., 2.], [3., 4.]])
    c = torch.tensor([[5., 6.], [7., 8.]])
    show("A * C", a * c)
    show("A @ C", a @ c)
    try:
        x @ torch.ones((3, 1))
    except RuntimeError as error:
        print("EXPECTED_SHAPE_ERROR:", str(error))
    else:
        raise AssertionError("The incompatible matrix product should fail.")


def experiment_c():
    x = torch.tensor([[1., 2.], [3., 4.], [5., 6.]])
    w1 = torch.tensor([[1., -1., 2.], [1., 1., -1.]])
    b1 = torch.tensor([0., -2., 0.])
    w2 = torch.tensor([[1.], [2.], [-1.]])
    b2 = torch.tensor([1.])
    z = x @ w1 + b1
    h = torch.relu(z)
    y = h @ w2 + b2
    show("Z", z)
    show("H = ReLU(Z)", h)
    show("Y", y)


def verify():
    x = torch.tensor([[1., 2.], [3., 4.], [5., 6.]])
    w = torch.tensor([[2.], [3.]])
    b = torch.tensor([1.])
    original_w = w.clone()
    y = x @ w + b
    torch.testing.assert_close(y, torch.tensor([[9.], [19.], [29.]]))
    changed = x @ torch.tensor([[4.], [3.]]) + b
    torch.testing.assert_close(changed - y, torch.tensor([[2.], [6.], [10.]]))
    torch.testing.assert_close(w, original_w)
    torch.testing.assert_close(x[:1] @ w + b, y[:1])
    # Independent practice E2/E3 numeric reference checks.
    a = torch.tensor([[2., 1.], [0., 3.]])
    c = torch.tensor([[1., 4.], [2., 5.]])
    torch.testing.assert_close(a * c, torch.tensor([[2., 4.], [0., 15.]]))
    torch.testing.assert_close(a @ c, torch.tensor([[4., 13.], [6., 15.]]))
    xr = torch.tensor([[1., 2., 3.], [4., 5., 6.]])
    wr = torch.tensor([[1., 0., -1.], [2., 1., 0.]])
    torch.testing.assert_close(xr @ wr.T, torch.tensor([[-2., 4.], [-2., 13.]]))
    try:
        xr @ wr
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected shape error in E3.")
    print("VERIFIED: forward values, parameter delta, unchanged weights, batch consistency, E2/E3 references, incompatible shape rejection")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("part", choices=["a", "b", "c", "verify"])
    parser.add_argument("--first-weight", type=float, default=2.0)
    args = parser.parse_args()
    print(f"Python={platform.python_version()}, torch={torch.__version__}, device=cpu")
    {"a": experiment_a, "b": lambda: experiment_b(args.first_weight),
     "c": experiment_c, "verify": verify}[args.part]()
