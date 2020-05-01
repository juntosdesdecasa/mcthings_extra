from mcpi.vec3 import Vec3

import pandas as pd

from mcthings.thing import Thing
from mcthings.scene import Scene


class CsvPoints(Thing):
    """
    The format of the CSV file must be:
    Level,X,Z,Y
    """
    file_path = None
    """ Path to the CSV file with the points to build"""
    level = "0"
    """ Which level to read """

    def draw_blocks(self, y, z, axis_x_list):
        """

        :param y: blocks y-axis position
        :param z: blocks z-axis position
        :param axis_x_list: list of x-axis in which a block must exist
        :return:
        """

        # Time to draw the blocks (y = height, z = Y are always the same in a group)
        init_y = self.position.y + y
        init_z = self.position.z + z
        end_y = self.position.y + y
        end_z = self.position.z + z

        # To detect splits (not incremental by 1 values) in the series order the x-axis positions
        axis_x_list.sort()
        init_split_x = axis_x_list[0]
        for i in range(1, len(axis_x_list) + 1):
            if ((i < len(axis_x_list) and (axis_x_list[i] - axis_x_list[i-1])) > 1 or
                    (i == len(axis_x_list))):
                init_x = self.position.x + init_split_x
                end_x = self.position.x + axis_x_list[i-1]

                Scene.server.postToChat("Building blocks defined in a CSV file (%s, %s, %s)" % (init_x, init_y, init_z))
                Scene.server.setBlocks(init_x, init_y, init_z,
                                       end_x, end_y, end_z,
                                       self.block)

                if i == len(axis_x_list):
                    break

                init_split_x = axis_x_list[i]

    def build(self):
        # Read the CSV file
        if not self.file_path:
            RuntimeError("Missing file_path param")

        pos = self.position

        # First approach: put a block in each position. Try to detect blocks that are groups in order
        # to build them using setBlocks

        # In order to explore the data pandas helps with group by and others operations
        df = pd.read_csv(self.file_path, delimiter=",")
        df.columns = ['Level', 'X', 'Z', 'Y']
        min_height = min(df['Y'])
        max_height = max(df['Y'])
        # Work only with Level 0)
        df0 = df[df['Level'].eq(0)]
        df1 = df[df['Level'].eq(1)]
        df2 = df[df['Level'].eq(2)]
        # Drop Level column
        df0.drop('Level', axis=1, inplace=True)
        df1.drop('Level', axis=1, inplace=True)
        df2.drop('Level', axis=1, inplace=True)
        # Let's analyze the data to find the best way to draw it
        # It seems that all the data has a range of X for a fixed z and Y
        # Let's confirm it using GROUP BY to analyze this Y,Z groups
        #
        # Blocks needed to build the Levels using horizontal columns along X
        # This is True is horizontal column is continuous but it can have splits
        # total_x_blocks_0 = len(df0.groupby(['Y', 'Z'])['X'].count())  # 828
        # total_x_blocks_1 = len(df1.groupby(['Y', 'Z'])['X'].count())  # 385
        # total_x_blocks_2 = len(df2.groupby(['Y', 'Z'])['X'].count())  # 683
        # Let's try to start building the Level 1 which is smaller
        # In the next df we have the list of Xs per Y and height. With it we can build one or more blocks
        # along the X-axis

        for name, group in df2.groupby(['Y', 'Z'])['X']:
            axis_y = name[0]
            axis_z = name[1]
            axis_x_list = group.values.tolist()

            # fixed position in Minecraft or y and z axis
            y = axis_y - min_height
            z = axis_z

            # The blocks along x could be just one or several splitted
            self.draw_blocks(y, z, axis_x_list)