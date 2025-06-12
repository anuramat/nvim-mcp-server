{
  description = "Nvimcp server";

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

        nvimcp = pythonPackages.buildPythonPackage rec {
          pname = "nvimcp";
          version = "0.1.0";

          src = ./.;

          propagatedBuildInputs = with pythonPackages; [
            pynvim
            mcp
          ];

          meta = {
            description = "Nvimcp server that exposes nvim functionality";
            homepage = "https://github.com/anuramat/nvimcp";
          };
        };

      in
      {
        packages.default = nvimcp;
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            (python3.withPackages (
              p: with p; [
                pynvim
                mcp
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
