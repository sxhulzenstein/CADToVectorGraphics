class MaterialProperties:
    def __init__( self, ka: float, kd: float, ks: float, alpha: float ) -> None:
        """
        Create an Object for describing the surface properties of the CAD-object

        Parameters:
            ka ( float ): ambient intensity factor
            kd ( float ): diffuese intensity factor
            ks ( float ): specular intensity factor
            alpha ( float ): shininess of the object
        """
        self.ka: float = ka
        self.kd: float = kd
        self.ks: float = ks
        self.alpha: float = alpha