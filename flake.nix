{
  description = "MCP server for Neovim";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        python = pkgs.python3;
        pythonPackages = python.pkgs;

        mcp-neovim = pythonPackages.buildPythonPackage rec {
          pname = "mcp-neovim";
          version = "0.1.0";

          src = ./.;

          propagatedBuildInputs = with pythonPackages; [
            pynvim
            mcp # Official Python MCP SDK
            msgpack
            setuptools
          ];

          meta = {
            description = "MCP server that exposes Neovim functionality";
            homepage = "https://github.com/anuramat/mcp.nvim";
          };
        };

      in
      {
        packages.default = mcp-neovim;

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            pythonPackages.pynvim
            pythonPackages.mcp # Official Python MCP SDK
            pythonPackages.msgpack
            pythonPackages.setuptools
            pythonPackages.pytest
            pythonPackages.pytest-asyncio
            pythonPackages.black
            pythonPackages.mypy
            pyright
            neovim # For testing
          ];

          shellHook = ''
            echo "MCP Neovim development environment"
            echo "Python: $(python --version)"
            echo "Available packages: pynvim, mcp, msgpack, pytest, black, mypy"
            echo ""
            export PYTHONPATH="$PWD:$PYTHONPATH"
          '';
        };
      }
    );
}
