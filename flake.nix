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

        nvim-mcp-server = pythonPackages.buildPythonPackage rec {
          pname = "nvim-mcp-server";
          version = "0.1.0";

          src = ./.;

          propagatedBuildInputs = with pythonPackages; [
            pynvim
            mcp
            msgpack
            setuptools
          ];

          meta = {
            description = "MCP server that exposes Neovim functionality";
            homepage = "https://github.com/anuramat/nvim-mcp-server";
          };
        };

      in
      {
        packages.default = nvim-mcp-server;
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            (python3.withPackages (
              p: with p; [
                pynvim
                mcp
                msgpack
                setuptools
                pytest
                pytest-asyncio
                black
                mypy
              ]
            ))
            pyright
            neovim
          ];
        };
      }
    );
}
