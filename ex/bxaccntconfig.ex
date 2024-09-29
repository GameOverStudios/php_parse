
defmodule PaidLevels.Schema.BxAccntConfig do
  use Ecto.Schema

  import Ecto.Changeset

  @primary_key {:id, :integer, autogenerate: true}
  @foreign_key_type :integer
  schema "bxaccntconfig" do

    timestamps()
  end

  @doc false
  def changeset(BxAccntConfig, attrs) do
    BxAccntConfig
    |> cast(attrs, [
      {:id, :integer},
           ])
    |> validate_required([:id])
  end
end
            